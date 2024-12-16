import csv
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from codebench_analytics.collector import Collector
from codebench_analytics.model.metrics import CodeMetrics, StudentCodeInfo
from codebench_analytics.utils.dataset import save

logger = logging.getLogger(__name__)


class ActionCollector(Collector):

    INACTIVITY_TIME = 300.0
    MIN_IT_TIME = 180.0
    MAX_CODE_TIME = 7200.0

    def collect(self) -> str:
        data: Dict[Tuple[int, int], StudentCodeInfo] = {}

        with open(self.csv_source, "r", newline="") as csv_file:
            logger.info("collecting student actions from '%s'", self.csv_source)
            reader = csv.DictReader(csv_file)

            for row in reader:
                row_question = int(row["question"])
                row_student = int(row["student"])
                key = (row_student, row_question)
                row_event_type = row["event_type"]
                row_time = row["event_time"]

                if key not in data:
                    data[key] = StudentCodeInfo()
                question_log = data[key]
                cur_time = datetime.strptime(row_time, "%Y-%m-%d %H:%M:%S.%f")

                # Ignore log if the student already settled the question or
                # there is a duplicated log in the codemirror
                if question_log.is_correct or (
                    question_log.last_time and cur_time < question_log.last_time
                ):
                    continue

                question_log.num_events += 1
                if question_log.last_time:
                    time_diff = cur_time - question_log.last_time
                    if time_diff.total_seconds() <= ActionCollector.INACTIVITY_TIME:
                        question_log.code_time += time_diff.total_seconds()

                question_log.last_time = cur_time
                if row_event_type == "blur":
                    question_log.last_time = None
                elif row_event_type == "change":
                    if row["event_op"] == "+delete":
                        question_log.num_deletes += 1
                elif row_event_type == "submit":
                    question_log.submitted = True
                    if row["event_info"] == "correct":
                        question_log.is_correct = True

        store_data: List[dict] = []
        csv_fields = ["student", "question", *StudentCodeInfo().to_dict.keys()]
        for key, metrics_info in data.items():
            if (
                metrics_info.submitted
                and metrics_info.code_time <= ActionCollector.MAX_CODE_TIME
            ):
                student, question = key
                store_data.append(
                    {
                        "student": student,
                        "question": question,
                        **metrics_info.to_dict,
                    }
                )
        save("output/metrics", "actions_by_student.csv", store_data, csv_fields)

        questions_info: Dict[int, CodeMetrics] = {}
        metrics_info: Optional[CodeMetrics] = CodeMetrics()
        for key, value in data.items():
            student, question_id = key
            if (
                not value.submitted
                and value.code_time >= ActionCollector.MIN_IT_TIME
            ):
                assert metrics_info is not None
                metrics_info.num_blank += 1
            if (
                value.code_time > ActionCollector.MAX_CODE_TIME
                or not value.submitted
            ):
                continue
            if question_id not in questions_info:
                questions_info[question_id] = CodeMetrics()
            metrics_info = questions_info[question_id]

            if value.is_correct:
                metrics_info.code_time += value.code_time
            metrics_info.num_events += value.num_events
            metrics_info.num_deletes += value.num_deletes

        csv_fields = list(CodeMetrics().to_dict.keys())
        return save(
            "output/metrics",
            "actions_data.csv",
            questions_info,
            ["question", *csv_fields],
        )


if __name__ == "__main__":
    src = "output/data/actions.csv"
    ActionCollector(src).collect()
