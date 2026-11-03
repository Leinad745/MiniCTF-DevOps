"""Configuracion central del microservicio CTF.

Aqui viven las "flags" (banderas) de cada desafio. En un CTF real estarian
protegidas; aqui son el objetivo educativo que el jugador debe extraer
explotando cada vulnerabilidad.
"""

# Flag del desafio de Inyeccion SQL: se guarda en la fila del usuario "admin"
# y solo se obtiene si el atacante logra evadir la autenticacion.
SQLI_FLAG = "FLAG{sql_1ny3cc10n_byp4ss}"

# Flag del desafio SSTI: se inyecta en el contexto de render de la plantilla.
SSTI_FLAG = "FLAG{ssti_t3mpl4t3_pwn3d}"

# Flag del desafio XSS: se entrega cuando se detecta un payload de script valido.
XSS_FLAG = "FLAG{xss_scr1pt_1ny3ct4d0}"

# Credenciales del usuario administrador (dueno de la flag de SQLi).
ADMIN_USER = "admin"
ADMIN_PASSWORD = "s3cr3t_p4ss_adm1n"
