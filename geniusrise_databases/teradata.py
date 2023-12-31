# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pyteradata
from geniusrise import BatchOutput, Spout, State


class Teradata(Spout):
    def __init__(self, output: BatchOutput, state: State, **kwargs):
        r"""
        Initialize the Teradata class.

        Args:
            output (BatchOutput): An instance of the BatchOutput class for saving the data.
            state (State): An instance of the State class for maintaining the state.
            **kwargs: Additional keyword arguments.

        ## Using geniusrise to invoke via command line
        ```bash
        genius Teradata rise \
            batch \
                --output_s3_bucket my_bucket \
                --output_s3_folder s3/folder \
            none \
            fetch \
                --args host=myteradata.example.com username=myusername password=mypassword database=mydb
        ```

        ## Using geniusrise to invoke via YAML file
        ```yaml
        version: "1"
        spouts:
            my_teradata_spout:
                name: "Teradata"
                method: "fetch"
                args:
                    host: "myteradata.example.com"
                    username: "myusername"
                    password: "mypassword"
                    database: "mydb"
                output:
                    type: "batch"
                    args:
                        bucket: "my_bucket"
                        s3_folder: "s3/folder"
        ```
        """
        super().__init__(output, state)
        self.top_level_arguments = kwargs

    def fetch(
        self,
        host: str,
        username: str,
        password: str,
        database: str,
    ):
        """
        📖 Fetch data from a Teradata database and save it in batch.

        Args:
            host (str): The Teradata host.
            username (str): The Teradata username.
            password (str): The Teradata password.
            database (str): The Teradata database name.

        Raises:
            Exception: If unable to connect to the Teradata server or execute the command.
        """
        # Initialize the Teradata connection
        try:
            conn = pyteradata.connect(host=host, username=username, password=password)
            conn.database = database
        except Exception as e:
            self.log.error(f"Error connecting to Teradata server: {e}")
            return

        # Perform the Teradata operation
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mytable")

            while True:
                row = cursor.fetchone()
                if not row:
                    break

                # Save the fetched row to a file
                self.output.save(row)

            # Update the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            current_state["success_count"] += 1
            self.state.set_state(self.id, current_state)

        except Exception as e:
            self.log.error(f"Error fetching data from Teradata: {e}")

            # Update the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            current_state["failure_count"] += 1
            self.state.set_state(self.id, current_state)

        finally:
            conn.close()
