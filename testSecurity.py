import security as s
m = s.Security()
try:
    m.run()
    print("exit good")
except KeyboardInterrupt:
    print("exit bad")
