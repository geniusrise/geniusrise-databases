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

from geniusrise import BatchOutput, Spout, State
from google.cloud import bigtable


class Bigtable(Spout):
    def __init__(self, output: BatchOutput, state: State, **kwargs):
        r"""
        Initialize the Bigtable class.

        Args:
            output (BatchOutput): An instance of the BatchOutput class for saving the data.
            state (State): An instance of the State class for maintaining the state.
            **kwargs: Additional keyword arguments.

        ## Using geniusrise to invoke via command line
        ```bash
        genius Bigtable rise \
            batch \
                --output_s3_bucket my_bucket \
                --output_s3_folder s3/folder \
            none \
            fetch \
                --args project_id=my_project instance_id=my_instance table_id=my_table
        ```

        ## Using geniusrise to invoke via YAML file
        ```yaml
        version: "1"
        spouts:
            my_bigtable_spout:
                name: "Bigtable"
                method: "fetch"
                args:
                    project_id: "my_project"
                    instance_id: "my_instance"
                    table_id: "my_table"
                output:
                    type: "batch"
                    args:
                        bucket: "my_bucket"
                        s3_folder: "s3/folder"
        ```
        """
        super().__init__(output, state)
        self.top_level_arguments = kwargs

    def fetch(self, project_id: str, instance_id: str, table_id: str):
        """
        📖 Fetch data from a Google Cloud Bigtable and save it in batch.

        Args:
            project_id (str): The Google Cloud Project ID.
            instance_id (str): The Bigtable instance ID.
            table_id (str): The Bigtable table ID.

        Raises:
            Exception: If unable to connect to the Bigtable server or fetch the data.
        """
        client = bigtable.Client(project=project_id)
        instance = client.instance(instance_id)
        table = instance.table(table_id)

        try:
            rows = table.read_rows()
            rows.consume_all()

            # Save the fetched rows to a file
            self.output.save(rows)

            # Update the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            current_state["success_count"] += 1
            self.state.set_state(self.id, current_state)

            # Log the total number of rows processed
            self.log.info(f"Total rows processed: {len(rows)}")

        except Exception as e:
            self.log.error(f"Error fetching data from Bigtable: {e}")

            # Update the state
            current_state = self.state.get_state(self.id) or {
                "success_count": 0,
                "failure_count": 0,
            }
            current_state["failure_count"] += 1
            self.state.set_state(self.id, current_state)
