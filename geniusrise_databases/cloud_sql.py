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

from typing import Any, Dict

import pymysql.cursors  # type: ignore
from geniusrise import BatchOutput, Spout, State


class GoogleCloudSQL(Spout):
    def __init__(self, output: BatchOutput, state: State, **kwargs: Any) -> None:
        r"""
        Initialize the GoogleCloudSQL class.

        Args:
            output (BatchOutput): An instance of the BatchOutput class for saving the data.
            state (State): An instance of the State class for maintaining the state.
            **kwargs: Additional keyword arguments.

        ## Using geniusrise to invoke via command line
        ```bash
        genius GoogleCloudSQL rise \
            batch \
                --output_s3_bucket my_bucket \
                --output_s3_folder s3/folder \
            none \
            fetch \
                --args host=127.0.0.1 port=3306 user=root password=root database=mydb query="SELECT * FROM table" page_size=100
        ```

        ## Using geniusrise to invoke via YAML file
        ```yaml
        version: "1"
        spouts:
            my_google_cloud_sql_spout:
                name: "GoogleCloudSQL"
                method: "fetch"
                args:
                    host: "127.0.0.1"
                    port: 3306
                    user: "root"
                    password: "root"
                    database: "mydb"
                    query: "SELECT * FROM table"
                    page_size: 100
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
        port: int,
        user: str,
        password: str,
        database: str,
        query: str,
        page_size: int = 100,
    ) -> None:
        """
        📖 Fetch data from a Google Cloud SQL database and save it in batch.

        Args:
            host (str): The Google Cloud SQL host.
            port (int): The Google Cloud SQL port.
            user (str): The Google Cloud SQL user.
            password (str): The Google Cloud SQL password.
            database (str): The Google Cloud SQL database name.
            query (str): The SQL query to execute.
            page_size (int): The number of rows to fetch per page. Defaults to 100.

        Raises:
            Exception: If unable to connect to the Google Cloud SQL or fetch the data.
        """
        # Initialize Google Cloud SQL connection
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor,
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                total_rows = cursor.rowcount
                processed_rows = 0

                while True:
                    rows = cursor.fetchmany(page_size)
                    if not rows:
                        break

                    # Save the fetched rows to a file
                    self.output.save(rows)

                    # Update the number of processed rows
                    processed_rows += len(rows)
                    self.log.info(f"Total rows processed: {processed_rows}/{total_rows}")

                # Update the state
                current_state: Dict[str, Any] = self.state.get_state(self.id) or {
                    "success_count": 0,
                    "failure_count": 0,
                    "processed_rows": 0,
                }
                current_state["success_count"] += 1
                current_state["processed_rows"] = processed_rows
                self.state.set_state(self.id, current_state)

            # Log the total number of rows processed
            self.log.info(f"Total rows processed: {processed_rows}/{total_rows}")

        except Exception as e:
            self.log.error(f"Error fetching data from Google Cloud SQL: {e}")

            # Update the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
                "processed_rows": 0,
            }
            current_state["failure_count"] += 1
            self.state.set_state(self.id, current_state)

        finally:
            connection.close()
