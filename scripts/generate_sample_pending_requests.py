import json, time

N = 58  # number of fake profiles to generate
start_ts = int(time.time()) + 10_000

data = {
    "relationships_follow_requests_sent": [
        {
            "title": "",
            "media_list_data": [],
            "string_list_data": [{
                "href": f"https://www.instagram.com/profile_{i:02d}",
                "value": f"profile_{i:02d}",
                "timestamp": start_ts - i * 3600
            }]
        }
        for i in range(1, N + 1)
    ]
}

json.dump(data, open("pending_follow_requests.sample.json", "w"), indent=2)
