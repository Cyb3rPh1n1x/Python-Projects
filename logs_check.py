from datetime import datetime

logs = [
    "2026-08-08 14:20:01 | user: alice   | ip: 192.168.1.10 | status: FAILED",
    "2026-08-08 14:20:07 | user: alice   | ip: 192.168.1.10 | status: FAILED",
    "2026-08-08 14:20:15 | user: bob     | ip: 10.0.0.5      | status: FAILED",
    "2026-08-08 14:20:18 | user: alice   | ip: 192.168.1.10 | status: FAILED",
    "2026-08-08 14:20:31 | user: charlie | ip: 172.16.0.8    | status: FAILED",
    "2026-08-08 14:20:42 | user: alice   | ip: 192.168.1.10 | status: FAILED",
    "2026-08-08 14:21:02 | user: david   | ip: 10.10.10.20   | status: SUCCESS",
    "2026-08-08 14:21:08 | user: bob     | ip: 10.0.0.5      | status: FAILED",
    "2026-08-08 14:21:15 | user: charlie | ip: 172.16.0.8    | status: FAILED",
    "2026-08-08 14:21:22 | user: david   | ip: 10.10.10.20   | status: FAILED",
    "2026-08-08 14:21:35 | user: bob     | ip: 10.0.0.5      | status: FAILED",
    "2026-08-08 14:21:48 | user: eve     | ip: 203.0.113.15  | status: FAILED",
    "2026-08-08 14:21:55 | user: charlie | ip: 172.16.0.8    | status: FAILED",
    "2026-08-08 14:22:10 | user: bob     | ip: 10.0.0.5      | status: FAILED",
    "2026-08-08 14:22:15 | user: eve     | ip: 198.51.100.22 | status: FAILED",
    "2026-08-08 14:22:30 | user: david   | ip: 10.10.10.20   | status: SUCCESS",
    "2026-08-08 14:22:41 | user: eve     | ip: 203.0.113.15  | status: SUCCESS",
    "2026-08-08 14:23:05 | user: alice   | ip: 192.168.1.10 | status: SUCCESS",
    "2026-08-08 14:23:20 | user: bob     | ip: 10.0.0.5      | status: SUCCESS",
    "2026-08-08 14:23:45 | user: eve     | ip: 198.51.100.22 | status: FAILED",
]

users = {}
adress = []
status = []

for log in logs:
    parts = log.split("|")

    user = parts[1].split(":")[1].strip()
    ip = parts[2].split(":")[1].strip()
    current_status = parts[3].split(":")[1].strip()

    users[ip] = user
    adress.append(ip)
    status.append(current_status)

warn_list = []
safe_list = []

for i in range(len(logs)):
    if adress[i] in safe_list or adress[i] in warn_list:
        continue

    alert = 0
    times = []

    for j in range(len(logs)):
        if adress[j] == adress[i] and status[j] == "FAILED":
            alert += 1

            time = logs[j].split("|")[0].strip()
            time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
            times.append(time)

    if len(times) >= 4:
        difference = (times[-1] - times[0]).total_seconds()

        if difference <= 50:
            warn_list.append(adress[i])
            print(
                "\033[91m" + users[adress[i]] + " : " + adress[i] +
                " is trying to brute force through the system\033[0m"
            )
        else:
            safe_list.append(adress[i])
            print(users[adress[i]], ":", adress[i], "is a normal user")
    else:
        safe_list.append(adress[i])
        print(users[adress[i]], ":", adress[i], "is a normal user")
    

    

            
            


        





