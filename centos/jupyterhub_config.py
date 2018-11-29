# Configuration file for jupyterhub.

c = get_config()

# use the sudo spawner
c.JupyterHub.spawner_class = 'sudospawner.SudoSpawner'

c.JupyterHub.authenticator_class = 'ldapauthenticator.LDAPAuthenticator'
c.LDAPAuthenticator.server_address = '35.227.181.238'
c.LDAPAuthenticator.server_port = 389
c.LDAPAuthenticator.use_ssl = False
c.LDAPAuthenticator.bind_dn_template = "CN={username},OU=jupyter,DC=example,dc=com"

c.SudoSpawner.debug_mediator = True
c.SudoSpawner.mediator_log_level = "DEBUG"
c.JupyterHub.log_level = 10
