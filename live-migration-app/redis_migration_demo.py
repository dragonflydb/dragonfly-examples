import redis
import time
import threading
import random
import string
import logging
import sys
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedisMigrationMonitor:
    def __init__(self, redis_host='localhost', redis_port=6379, target_keys=3_000):
        """
        Initializes the monitor with a target for total keys inserted, plus a grid-based display
        that tracks how many keys have been inserted.
        
        Each cell in the grid will represent a portion of the total key goal.
        """
        try:
            logger.info(f"Initializing monitor with host={redis_host}, port={redis_port}")
            self.redis_host = redis_host
            self.redis_port = redis_port

            self.redis_client = redis.Redis(host=redis_host, port=redis_port)
            self.redis_client.ping()

            # Move this line so target_keys is defined before computing chunk_size_keys
            self.target_keys = target_keys  # ← Set target keys first

            # Set up the grid dimensions
            self.grid_width = 80
            self.grid_height = 20

            total_cells = self.grid_width * self.grid_height

            # Now that self.target_keys is defined, we can safely compute this
            self.chunk_size_keys = max(1, self.target_keys // total_cells)

            # Initialize a 2D array for the display: filled with '░'
            self.memory_cells = [
                ['░' for _ in range(self.grid_width)]
                for _ in range(self.grid_height)
            ]

            self.running = True
            self.counter = 0
            self.verification_threads = []
            self.keep_inserting = True 

            logger.info("Monitor initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {str(e)}")
            raise

    def generate_random_value(self, size_kb=1):
        """
        Generate a random ASCII string of size_kb kilobytes.
        """
        return ''.join(random.choices(string.ascii_letters + string.digits, k=size_kb * 1024))

    def get_redis_memory_usage(self):
        """
        Retrieve the used_memory from Redis INFO command (in bytes).
        """
        info = self.redis_client.info(section="memory")
        return info['used_memory']

    def insert_data(self):
        """
        Insert data until we've hit our target key count.
        """
        while self.running and self.keep_inserting:
            try:
                if self.counter >= self.target_keys:
                    logger.info("Reached target number of keys. Stopping insertion.")
                    self.keep_inserting = False
                    break

                # Insert in smaller batches
                batch_size = 10000
                pipe = self.redis_client.pipeline()

                for _ in range(batch_size):
                    if self.counter >= self.target_keys:
                        break
                    key = f"test_key_{self.counter}"
                    pipe.set(key, self.generate_random_value(size_kb=1))
                    self.counter += 1

                pipe.execute()
                time.sleep(0.05)

            except Exception as e:
                logger.error(f"Error inserting data: {e}")
                time.sleep(0.1)

    def update_row(self, row_number):
        """
        Continuously updates one row of the grid based on the actual number of keys in Redis.
        Each cell represents chunk_size_keys worth of inserted keys.
        """
        while self.running:
            # Always query Redis for current key count
            current_keys = self.redis_client.dbsize()

            new_row = []
            for col in range(self.grid_width):
                chunk_index = row_number * self.grid_width + col
                chunk_start = chunk_index * self.chunk_size_keys
                chunk_end = chunk_start + self.chunk_size_keys

                # If we've inserted at least chunk_start worth of keys, the cell is partially filled
                # If we've inserted at least chunk_end worth of keys, the cell is fully filled
                # but for simplicity, treat partial fill as the same symbol:
                if current_keys >= chunk_start:
                    if current_keys >= chunk_end:
                        new_row.append('█')  # fully filled
                    else:
                        new_row.append('█')  # partial fill, same char
                else:
                    new_row.append('░')

            self.memory_cells[row_number] = new_row
            time.sleep(0.1)

    def start_verification_threads(self):
        """
        Spin up a verification thread per row to continuously update it
        based on the current key count (self.counter).
        """
        for row in range(self.grid_height):
            t = threading.Thread(target=self.update_row, args=(row,))
            t.daemon = True
            t.start()
            self.verification_threads.append(t)

    def update_redis_config(self, host, port, password=None):
        """
        Update the Redis connection on the fly, so we can 'migrate' to a new Redis.
        """
        try:
            logger.info(f"Switching Redis connection to host={host}, port={port}")
            # Pause insertion while reconfiguring
            self.redis_host = host
            self.redis_port = port
            self.redis_password = password
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                password=password  # Pass the password if given
            )
            self.redis_client.ping()
            logger.info("Redis connection updated successfully")

            # Instead of resetting to 0, read how many keys are already in the new Redis
            new_key_count = self.redis_client.dbsize()
            logger.info(f"Found {new_key_count} existing keys in new Redis instance")

            self.counter = new_key_count  # Reflect the existing keys

            # Decide whether to keep inserting based on existing key count
            if self.counter < self.target_keys:
                self.keep_inserting = True
            else:
                self.keep_inserting = False
                logger.info("New Redis already has enough keys. Not inserting more.")

        except Exception as e:
            logger.error(f"Failed to update Redis config: {e}")

    def visualize(self):
        """
        Draw a progress bar based on total keys inserted vs. target_keys (key-based only).
        Now also queries Redis directly so it instantly reflects flushes or existing keys.
        """
        last_draw = time.time()
        while self.running:
            now = time.time()
            if now - last_draw >= 1.0:
                last_draw = now

                actual_key_count = self.redis_client.dbsize()
                print("\033[2J\033[H", end='')
                print("Redis Live Migration Demo - Key-Based Progress")
                print("=" * 80)
                print(f"Connected to: redis://{self.redis_host}:{self.redis_port}")
                print("-" * 80)

                # For clarity, we can still show memory usage, but we'll focus on keys:
                used_bytes = self.get_redis_memory_usage()
                used_mb = used_bytes / (1024 * 1024)
                print(f"Memory Usage: {used_mb:.2f} MB (Informational)")

                # Show how many keys Redis actually has right now:
                print(f"Total Keys Inserted (Real): {actual_key_count} / {self.target_keys}")
                key_ratio = min(actual_key_count / self.target_keys, 1.0)
                bar_width = 50
                filled = int(key_ratio * bar_width)
                print(f"[{'█' * filled}{'░' * (bar_width - filled)}] {key_ratio * 100:5.1f}%")

                # Now show the row-based "key-chunk" grid
                print()
                print("Key-Based Grid")
                border = "─" * self.grid_width
                print(f"┌{border}┐")
                for row in range(self.grid_height):
                    line = ''.join(self.memory_cells[row])
                    print(f"│{line}│")
                print(f"└{border}┘")

            time.sleep(0.1)


# ----------------------------- Flask App Below ----------------------------- #

app = Flask(__name__)
monitor = None

@app.route('/update_redis', methods=['POST'])
def update_redis():
    """
    Accepts JSON: {"host": "<hostname>", "port": <number>, "password": "<optional_password>"}
    Updates the monitor's Redis configuration on the fly.
    """
    global monitor
    if not monitor:
        return jsonify({"error": "Monitor not initialized"}), 500

    data = request.get_json()
    if not data or 'host' not in data:
        return jsonify({"error": "Host is required"}), 400

    new_host = data['host']
    new_port = data.get('port', 6379)
    new_password = data.get('password', None)  # Retrieve optional password

    # Pass the password if specified
    monitor.update_redis_config(new_host, new_port, password=new_password)

    return jsonify({
        "message": "Redis config updated",
        "host": new_host,
        "port": new_port,
        "password_included": bool(new_password)
    })


def main():
    global monitor
    try:
        monitor = RedisMigrationMonitor(
            redis_host="localhost",
            redis_port=6379,
            target_keys=3_000_00,
            flush_on_start=False
        )

        # Automatically start row-update (grid) threads
        monitor.start_verification_threads()

        # Start data insertion thread
        insert_thread = threading.Thread(target=monitor.insert_data)
        insert_thread.daemon = True
        insert_thread.start()

        # Start visualization in a separate thread
        viz_thread = threading.Thread(target=monitor.visualize)
        viz_thread.daemon = True
        viz_thread.start()

        # Finally, run the Flask server
        app.run(host='0.0.0.0', port=8080, debug=False)

    except Exception as e:
        logger.error(f"Failed to start the Redis Migration Monitor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 