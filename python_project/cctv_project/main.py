import json
import os
import logging
import threading
import time
import shutil
import subprocess
from datetime import datetime

# Change working directory to the script's directory
# to ensure relative paths work correctly.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- Configuration ---
FFMPEG_PATH = r"C:\Users\Praveen\Downloads\ffmpeg-8.0.1\bin"
CAMERAS_CONFIG_FILE = 'cameras.json'
LOG_FILE = 'logs/app.log'
RECORDING_INTERVAL_SECONDS = 10 # Create a new recording file every 10 seconds

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def load_cameras(config_file):
    """Loads camera configurations from a JSON file."""
    try:
        with open(config_file, 'r') as f:
            cameras = json.load(f)
        logging.info(f"Successfully loaded {len(cameras)} camera configurations.")
        return cameras
    except FileNotFoundError:
        logging.error(f"Error: Configuration file not found at '{config_file}'")
        return []
    except json.JSONDecodeError:
        logging.error(f"Error: Could not decode JSON from '{config_file}'")
        return []

def get_video_duration(video_path):
    """Gets the duration of a video file using ffprobe."""
    ffprobe_exe = os.path.join(FFMPEG_PATH, 'ffprobe.exe')
    command = [
        ffprobe_exe,
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout)
    except FileNotFoundError:
        logging.error("ffprobe command not found. Please ensure FFmpeg is installed and in your system's PATH.")
        return 0.0
    except (subprocess.CalledProcessError, ValueError) as e:
        logging.error(f"Error getting video duration: {e}")
        if isinstance(e, subprocess.CalledProcessError):
            logging.error(f"ffprobe stderr: {e.stderr}")
        return 0.0

def simulate_camera_recording(camera_config, stop_event):
    """Simulates recording for a single camera."""
    camera_id = camera_config.get('camera_id', 'UNKNOWN_CAM')
    source_path = camera_config.get('source')
    recording_path = camera_config.get('recording_path')
    s3_path = camera_config.get('s3_path')

    if not all([source_path, recording_path, s3_path]):
        logging.error(f"[{camera_id}] Missing 'source', 'recording_path', or 's3_path' in config.")
        return

    if not os.path.exists(source_path):
        logging.error(f"[{camera_id}] Source file not found: {source_path}")
        return

    if not os.path.exists(recording_path):
        os.makedirs(recording_path)
    if not os.path.exists(s3_path):
        os.makedirs(s3_path)

    video_duration = get_video_duration(source_path)
    if video_duration == 0:
        logging.error(f"[{camera_id}] Could not get duration of source video.")
        return

    logging.info(f"[{camera_id}] Starting recording simulation.")
    start_time = 0

    while not stop_event.is_set():
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{camera_id}_{timestamp}.mp4"
            temp_path = os.path.join(recording_path, filename)

            # Use FFmpeg to create a clip
            ffmpeg_exe = os.path.join(FFMPEG_PATH, 'ffmpeg.exe')
            command = [
                ffmpeg_exe,
                '-ss', str(start_time),
                '-i', source_path,
                '-t', str(RECORDING_INTERVAL_SECONDS),
                '-c', 'copy',
                temp_path
            ]
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info(f"[{camera_id}] Created recording segment: {temp_path}")

            # Simulate S3 upload by moving the file
            s3_destination = os.path.join(s3_path, filename)
            shutil.move(temp_path, s3_destination)
            logging.info(f"[{camera_id}] Moved recording to S3: {s3_destination}")

            start_time = (start_time + RECORDING_INTERVAL_SECONDS) % video_duration

            # Wait for the next recording interval
            time.sleep(RECORDING_INTERVAL_SECONDS)
        except subprocess.CalledProcessError as e:
            logging.error(f"[{camera_id}] FFmpeg error: {e.stderr.decode()}")
            break
        except Exception as e:
            logging.error(f"[{camera_id}] An error occurred during recording: {e}")
            break

    logging.info(f"[{camera_id}] Stopping recording simulation.")


def main():
    """Main function to start the CCTV simulation."""
    logging.info("--- Starting CCTV Recording Simulation ---")
    cameras = load_cameras(CAMERAS_CONFIG_FILE)
    
    if not cameras:
        logging.error("No camera configurations loaded. Exiting.")
        return

    threads = []
    stop_event = threading.Event()

    # Create and start a thread for each camera
    for camera in cameras:
        thread = threading.Thread(
            target=simulate_camera_recording,
            args=(camera, stop_event),
            name=camera.get('camera_id', 'Thread')
        )
        threads.append(thread)
        thread.start()

    # Let the simulation run indefinitely until interrupted
    try:
        while True:
            time.sleep(1) # Keep the main thread alive
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received. Shutting down.")
    finally:
        # Signal all threads to stop
        logging.info("Stopping all camera threads...")
        stop_event.set()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

    logging.info("--- CCTV Recording Simulation Finished ---")

if __name__ == '__main__':
    main()