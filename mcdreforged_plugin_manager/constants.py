from mcdreforged.api.all import *


psi = ServerInterface.get_instance().as_plugin_server_interface()
meta = psi.get_self_metadata()

PREFIX = '!!mpm'

PLUGIN_LABELS = ['information', 'tool', 'management', 'api']
