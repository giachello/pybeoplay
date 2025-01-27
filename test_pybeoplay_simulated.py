import responses

from pybeoplay import BeoPlay
from pybeoplay.const import BEOPLAY_URL_STAND, BEOPLAY_URL_STAND_ACTIVE
import logging

LOG = logging.getLogger(__name__)


@responses.activate
def test_standpositions(gateway: BeoPlay):
    # register via direct arguments
    with open('standpositionstest.json', 'r') as file:
        content = file.read()    
        file.close()
    responses.add(
        responses.GET,
        "http://192.168.1.98:8080/" + BEOPLAY_URL_STAND,
        body=content.encode('utf-8'),
        status=200,
    )

    with open('standpositiontest.json', 'r') as file:
        content = file.read()  
        file.close()  
    responses.add(
        responses.GET,
        "http://192.168.1.98:8080/" + BEOPLAY_URL_STAND_ACTIVE,
        body=content.encode('utf-8'),
        status=200,
    )


    print ("--- STAND POSITIONS ---")
    gateway.getStandPositions()
    print (gateway.standPositions)

    gateway.getStandPosition()
    print ("Stand Position: ", gateway.standPosition)




if __name__ == '__main__':
    import sys
    ch = logging.StreamHandler(sys.stdout)
    logging.basicConfig(level=logging.DEBUG)
    ch.setLevel(logging.DEBUG)
    LOG.addHandler(ch)

    if len(sys.argv) < 2:
        quit()

    gateway = BeoPlay(sys.argv[1])

    test_standpositions(gateway)   

