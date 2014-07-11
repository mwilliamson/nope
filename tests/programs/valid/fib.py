def fib(n: int) -> int:
    seq = [0, 1]
    for i in range(2, n + 1):
        seq[i] = seq[i - 1] + seq[i - 2]
    
    return seq[n]
