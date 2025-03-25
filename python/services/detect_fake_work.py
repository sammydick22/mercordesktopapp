#!/usr/bin/env python3
import time
import threading
import math
from math import log2
import sys
from pynput import mouse, keyboard
import tiktoken
import os
from cerebras.cloud.sdk import Cerebras

# ----------------------------
# Active Window Detection (Windows Only)
# ----------------------------
if sys.platform == 'win32':
    import ctypes
    import ctypes.wintypes

    def get_active_window_title():
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
else:
    def get_active_window_title():
        # For non-Windows platforms, this function can be expanded as needed.
        return "Unknown"

# ----------------------------
# Fake Work Detector Class
# ----------------------------
class FakeWorkDetector:
    def __init__(self,
                 afk_threshold=300,               # seconds before AFK is flagged
                 mouse_variance_threshold=5,      # low variance indicates repetitive mouse movement
                 mouse_sample_size=20,            # number of recent mouse positions to analyze
                 gibberish_ratio_threshold=1.5,   # average tokens per word threshold
                 gibberish_entropy_threshold=6.0, # token distribution entropy threshold
                 max_recent_words=50,             # maximum words in the rolling window
                 min_recent_words=10,             # minimum words required to perform token analysis
                 allowed_window_titles=None,      # optional list of allowed active window titles
                 keystroke_variance_threshold=0.001,# threshold for keystroke timing variance
                 log_active_window=True,          # enable active window usage logging
                 token_cerebras_cooldown=600      # cooldown in seconds for Cerebras token checks
                 ):
        # Monitoring parameters
        self.afk_threshold = afk_threshold
        self.mouse_variance_threshold = mouse_variance_threshold
        self.mouse_sample_size = mouse_sample_size

        # Token-based gibberish detection parameters
        self.gibberish_ratio_threshold = gibberish_ratio_threshold
        self.gibberish_entropy_threshold = gibberish_entropy_threshold
        self.max_recent_words = max_recent_words
        self.min_recent_words = min_recent_words

        # Keystroke dynamics parameter
        self.keystroke_variance_threshold = keystroke_variance_threshold

        # Active window allowed list (if provided)
        self.allowed_window_titles = allowed_window_titles

        # Whether to log active window usage
        self.log_active_window = log_active_window

        # Cooldown for Cerebras token-check calls
        self.token_cerebras_cooldown = token_cerebras_cooldown
        self.last_token_cerebras_call = 0

        # State variables
        self.last_active = time.time()
        self.mouse_positions = []        # List of (x, y, timestamp)
        self.typed_text_buffer = ""      # Buffer for keystrokes until a delimiter
        self.recent_words = []           # Rolling window of recent words
        self.keystroke_times = []        # Timestamps for keystroke dynamics
        self.fake_work_detected = False
        self.listening_enabled = False

        # Active window logging state
        self.active_window_log = {}      # Maps window title to total seconds spent
        self.current_active_window = None
        self.current_window_start_time = None

        # Listener handles and threads
        self.mouse_listener = None
        self.keyboard_listener = None
        self.afk_thread = None
        self.active_window_thread = None
        self.cerebras_activity_thread = None

        # Initialize the tokenizer (using a pre-trained LLM encoding)
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def update_last_active(self):
        self.last_active = time.time()

    # ----------------------------
    # Mouse Monitoring
    # ----------------------------
    def on_move(self, x, y):
        self.update_last_active()
        self.mouse_positions.append((x, y, time.time()))
        if len(self.mouse_positions) > self.mouse_sample_size:
            self.mouse_positions.pop(0)
        self.check_mouse_repetitiveness()

    def check_mouse_repetitiveness(self):
        if len(self.mouse_positions) < self.mouse_sample_size:
            return
        xs = [pos[0] for pos in self.mouse_positions]
        ys = [pos[1] for pos in self.mouse_positions]
        mean_x = sum(xs) / len(xs)
        mean_y = sum(ys) / len(ys)
        var_x = sum((x - mean_x) ** 2 for x in xs) / len(xs)
        var_y = sum((y - mean_y) ** 2 for y in ys) / len(ys)
        if var_x < self.mouse_variance_threshold and var_y < self.mouse_variance_threshold:
            self.fake_work_detected = True

    def on_click(self, x, y, button, pressed):
        self.update_last_active()

    def on_scroll(self, x, y, dx, dy):
        self.update_last_active()

    # ----------------------------
    # Keyboard Monitoring & Keystroke Dynamics
    # ----------------------------
    def on_press(self, key):
        self.update_last_active()
        current_time = time.time()
        self.keystroke_times.append(current_time)
        if len(self.keystroke_times) > 50:
            self.keystroke_times = self.keystroke_times[-50:]
        self.check_keystroke_timing()

        try:
            char = key.char  # Only alphanumeric keys have .char
            if char:
                self.typed_text_buffer += char
        except AttributeError:
            if key in [keyboard.Key.space, keyboard.Key.enter]:
                self.process_typed_buffer()
                self.typed_text_buffer = ""

    def check_keystroke_timing(self):
        if len(self.keystroke_times) < 6:
            return
        intervals = [self.keystroke_times[i] - self.keystroke_times[i - 1] for i in range(1, len(self.keystroke_times))]
        avg_interval = sum(intervals) / len(intervals)
        variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
        if variance < self.keystroke_variance_threshold:
            self.fake_work_detected = True

    def process_typed_buffer(self):
        words = self.typed_text_buffer.split()
        if not words:
            return
        for word in words:
            if self.is_gibberish_word(word):
                self.fake_work_detected = True
                return
        self.recent_words.extend(words)
        if len(self.recent_words) > self.max_recent_words:
            self.recent_words = self.recent_words[-self.max_recent_words:]
        self.check_token_metrics()

    def is_gibberish_word(self, word):
        vowels = "aeiouAEIOU"
        if len(word) > 3 and not any(v in word for v in vowels):
            return True
        return False

    # ----------------------------
    # Token Analysis for Novel Detection
    # ----------------------------
    def check_token_metrics(self):
        if len(self.recent_words) < self.min_recent_words:
            return
        text = " ".join(self.recent_words)
        token_ids = self.encoder.encode(text)
        total_tokens = len(token_ids)
        avg_tokens_per_word = total_tokens / len(self.recent_words)
        token_freq = {}
        for token in token_ids:
            token_freq[token] = token_freq.get(token, 0) + 1
        total = float(total_tokens)
        entropy = -sum((count / total) * log2(count / total) for count in token_freq.values())
        # Debugging info (optional):
        # print(f"Avg tokens/word: {avg_tokens_per_word:.2f}, Entropy: {entropy:.2f}")

        if avg_tokens_per_word > self.gibberish_ratio_threshold or entropy > self.gibberish_entropy_threshold:
            now = time.time()
            # Only call the Cerebras endpoint if cooldown has passed
            if now - self.last_token_cerebras_call > self.token_cerebras_cooldown:
                self.last_token_cerebras_call = now
                # Make the Cerebras call with the text
                if not self.cerebras_token_check(text):
                    self.fake_work_detected = True
            # Else, skip the Cerebras call to avoid spamming

    def cerebras_token_check(self, text):
        """
        Calls the Cerebras endpoint with the provided text.
        Expects a JSON response with key 'valid' (true/false).
        Returns True if the text is valid; otherwise False.
        """
        prompt = (
            "Based on the following typed words, determine if the input is valid natural language or gibberish. "
            "Return a JSON object with key 'valid' set to true if the text is valid, or false if it is gibberish. "
            f"Text: {text}"
        )
        try:
            client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY"))
            response = client.chat.completions.create(
                messages=[{"role": "system", "content": prompt}],
                model="llama3.1-8b",
                stream=False,
                max_completion_tokens=1024,
                temperature=0,
                top_p=0.42,
                response_format={"type": "json_object"}
            )
            # Expecting a response like {"valid": true} or {"valid": false}
            return response.get("valid", True)
        except Exception as e:
            print("Error querying Cerebras for token check:", e)
            return True  # On error, assume valid to avoid false positives

    # ----------------------------
    # AFK (Inactivity) Monitoring
    # ----------------------------
    def afk_check(self):
        while self.listening_enabled and not self.fake_work_detected:
            if time.time() - self.last_active > self.afk_threshold:
                self.fake_work_detected = True
                break
            time.sleep(1)

    # ----------------------------
    # Active Window Monitoring & Logging
    # ----------------------------
    def active_window_logger(self):
        self.current_active_window = get_active_window_title()
        self.current_window_start_time = time.time()
        while self.listening_enabled:
            time.sleep(1)
            active_title = get_active_window_title()
            if active_title != self.current_active_window:
                duration = time.time() - self.current_window_start_time
                self.active_window_log[self.current_active_window] = self.active_window_log.get(self.current_active_window, 0) + duration
                self.current_active_window = active_title
                self.current_window_start_time = time.time()
            if self.allowed_window_titles and active_title not in self.allowed_window_titles:
                self.fake_work_detected = True
        duration = time.time() - self.current_window_start_time
        self.active_window_log[self.current_active_window] = self.active_window_log.get(self.current_active_window, 0) + duration

    # ----------------------------
    # Cerebras Activity Log Check (Every 10 Minutes)
    # ----------------------------
    def cerebras_activity_check(self):
        """
        Every 10 minutes, send the active window log to the Cerebras endpoint
        to ask if the user was on valid work-related applications.
        """
        while self.listening_enabled and not self.fake_work_detected:
            time.sleep(600)  # 10 minutes
            prompt = (
                "Based on the following activity log (window title: total seconds spent), "
                "determine if the user was on valid work-related applications. "
                "Return a JSON object with key 'valid' and value true if all the apps are valid, "
                "or false if not. "
                f"Activity Log: {self.active_window_log}"
            )
            try:
                client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY"))
                response = client.chat.completions.create(
                    messages=[{"role": "system", "content": prompt}],
                    model="llama3.1-8b",
                    stream=False,
                    max_completion_tokens=1024,
                    temperature=0,
                    top_p=0.42,
                    response_format={"type": "json_object"}
                )
                if not response.get("valid", True):
                    self.fake_work_detected = True
            except Exception as e:
                print("Error querying Cerebras for activity log:", e)

    # ----------------------------
    # External Control & Aggregation
    # ----------------------------
    def enable_listening(self):
        if self.listening_enabled:
            return
        self.listening_enabled = True
        self.fake_work_detected = False
        self.last_active = time.time()
        self.mouse_positions = []
        self.typed_text_buffer = ""
        self.recent_words = []
        self.keystroke_times = []
        self.active_window_log = {}
        self.current_active_window = None
        self.current_window_start_time = None

        self.mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        self.mouse_listener.start()

        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.keyboard_listener.start()

        self.afk_thread = threading.Thread(target=self.afk_check, daemon=True)
        self.afk_thread.start()

        if self.log_active_window:
            self.active_window_thread = threading.Thread(target=self.active_window_logger, daemon=True)
            self.active_window_thread.start()

        self.cerebras_activity_thread = threading.Thread(target=self.cerebras_activity_check, daemon=True)
        self.cerebras_activity_thread.start()

    def disable_listening(self):
        self.listening_enabled = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

    def detect_fake_work(self):
        """
        Generator that runs in the background and yields True when fake work is detected.
        """
        self.enable_listening()
        try:
            while self.listening_enabled and not self.fake_work_detected:
                time.sleep(0.5)
            if self.fake_work_detected:
                yield True
        finally:
            self.disable_listening()

    def get_active_window_log(self):
        """
        Returns the active window usage log as a dictionary.
        """
        return self.active_window_log

# ----------------------------
# Example Usage
# ----------------------------
if __name__ == '__main__':
    allowed_windows = ["Microsoft Word", "Excel", "Visual Studio Code", "Your Work App"]
    detector = FakeWorkDetector(allowed_window_titles=allowed_windows)
    print("Monitoring for fake work in the background...")
    for detection in detector.detect_fake_work():
        if detection:
            print("Fake work detected!")
            break

    log = detector.get_active_window_log()
    print("Active window usage log:")
    for window, duration in log.items():
        print(f"  {window}: {duration:.1f} seconds")
