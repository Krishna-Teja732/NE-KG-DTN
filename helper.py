from fetch_data import Hashcompute

if __name__ == "__main__":
    HC = Hashcompute()
    ch = 32
    
    while True:
        ch = ord(input("Press space to continue: "))
        if ch == 32:
            flow_remove = HC.compare()
            print("Flow entry remove: ")
            print(flow_remove)
        
