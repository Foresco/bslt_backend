from datetime import datetime as dt
from jsonserv.pdm.models import PartObject
from jsonserv.exchange.models import ExternalPartner, ExchangeSession, ExternalID

par = ExternalPartner.objects.get(pk=1)
sess = ExchangeSession(partner=par, direction='I', exchange_datetime=dt.now().date())
sess.save()

internal = PartObject.objects.get(pk=2) 

obj, created = ExternalID.objects.get_or_create(internal=internal, partner=par, external_id='aaa', exchange_session=sess)
