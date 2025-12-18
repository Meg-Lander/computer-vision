# core/stats_manager.py
import csv
import datetime

class StatsManager:
    def __init__(self):
        self.history = []

    def add_record(self, source_name, qr_data_list, process_time):
        if not qr_data_list:
            self.history.append({
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                "source": source_name,
                "count": 0,
                "conf_avg": 0.0,
                "geo_score_avg": 0.0,
                "duration": process_time
            })
            return

        avg_conf = sum([item['conf'] for item in qr_data_list]) / len(qr_data_list)
        avg_geo = sum([item['geo_score'] for item in qr_data_list]) / len(qr_data_list)

        record = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source_name,
            "count": len(qr_data_list),
            "conf_avg": round(avg_conf, 4),
            "geo_score_avg": round(avg_geo, 4),
            "duration": round(process_time, 4)
        }
        self.history.append(record)

    def get_history(self):
        return self.history

    def export_csv(self, filename):
        if not self.history:
            return False
        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                fieldnames = ["timestamp", "source", "count", "conf_avg", "geo_score_avg", "duration"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.history)
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False