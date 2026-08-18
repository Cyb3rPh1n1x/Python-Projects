money = [1,3,4]#change depending on the coins available
change = 17#set it as the wanted change
dp = [float("inf")] * (change+1)
dp[0] = 0
coins = {0:[0]}
for amount in range(1,change+1):
    for coin in money:
        if dp[amount-coin]+1<dp[amount]:
            dp[amount]=dp[amount-coin]+1
            result = []
            for item in coins[amount-coin]:
                if item != 0:
                    result.append(item)
            result.append(coin)
            coins[amount] = result

print(dp[change])
print(coins[change])