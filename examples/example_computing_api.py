import requests

workflow = {"user_uid": "high_res_user",
            "job_list": [
                {
                    "mlex_app": "high-res-segmentation",
                    "description": "test_1",
                    "service_type": "backend",
                    "working_directory": "/data/mlex_repo/mlex_tiled/data",
                    "job_kwargs": 
                        {
                            "uri": "mlexchange1/random-forest-dc:1.1",
                            "type": "docker",
                            "cmd": "python random_forest.py data/seg-results/spiral/image-train data/seg-results-test/spiral/feature data/seg-results/spiral/mask data/seg-results-test/spiral/model '{\"n_estimators\": 30, \"oob_score\": true, \"max_depth\": 8}'",
                            "kwargs": {"job_type": "train",
                                       "experiment_id": "123",
                                       "dataset": "name_of_dataset",
                                       "params": "{\"n_estimators\": 30, \"oob_score\": true, \"max_depth\": 8}"}
                        }
                },
                {
                    "mlex_app": "high-res-segmentation",
                    "description": "test_1",
                    "service_type": "backend",
                    "working_directory": "/data/mlex_repo/mlex_tiled/data",
                    "job_kwargs": 
                        {
                            "uri": "mlexchange1/random-forest-dc:1.1",
                            "type": "docker",
                            "cmd": "python segment.py data/data/20221222_085501_looking_from_above_spiralUP_CounterClockwise_endPointAtDoor_0-1000 data/seg-results-test/spiral/model/random-forest.model data/seg-results-test/spiral/output '{\"show_progress\": 1}'",
                            "kwargs": {"job_type": "train",
                                       "experiment_id": "124",
                                       "dataset": "name_of_dataset",
                                       "params": "{\"show_progress\": 1}"}
                        }
                },
            ],
            "host_list": ["vaughan.als.lbl.gov"],
                        "dependencies": {
                                            "0": [],
                                            "1": [0]
                                        },
                        "requirements": {
                                            "num_processors": 2,
                                            "num_gpus": 0,
                                            "num_nodes": 1
                                        }
    }


job_submitted = requests.post("http://job-service:8080/api/v0/workflows", json=workflow)

if job_submitted.status_code == 200:
    print(f'Workflow has been succesfully submitted with uid: {job_submitted.json()}')
else:
    print(f'Workflow presented error code: {job_submitted.status_code}')
    print(f'Error code: {job_submitted.json()}')


