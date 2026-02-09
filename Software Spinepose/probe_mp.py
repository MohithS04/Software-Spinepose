import mediapipe
import os
import sys

print(f"MediaPipe Version: {mediapipe.__version__}")
print(f"MediaPipe Location: {os.path.dirname(mediapipe.__file__)}")
print("Dir(mediapipe):", dir(mediapipe))

try:
    import mediapipe.solutions
    print("Success: import mediapipe.solutions")
    print("Dir(mediapipe.solutions):", dir(mediapipe.solutions))
except ImportError as e:
    print(f"Failed: import mediapipe.solutions -> {e}")

try:
    import mediapipe.python.solutions
    print("Success: import mediapipe.python.solutions")
except ImportError as e:
    print(f"Failed: import mediapipe.python.solutions -> {e}")
