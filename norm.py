from datetime import datetime



def timer():
    tom = datetime.now()
    return tom
print(timer().ctime())