import security as s
import logging
m = s.Security()
try:
    m.run()
    print("exit good")
    logging.info("test security exit good")
except KeyboardInterrupt:
    logging.error("test security exit bad")
    print("exit bad")
