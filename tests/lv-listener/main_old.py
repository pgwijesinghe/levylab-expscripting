from lvcomm import Experiment

exp = Experiment()
exp.set_temp(temp=350,rate=30)
# exp.set_field(field=0.5,rate=0.01)
exp.set_AO(channel=2,DC=0)