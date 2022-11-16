# /{corso}/{anno}/{anno_accademico}/{percorso}/?{lang}

# campi del calendario:
# - lez/ese/tipo_short
# - insegnamento
# - percorso
# - docente
# - aula completa

# campi da parsare: percorsi json [ricorda timezone UTC+1]
# $ = $.celle
# $.[].ora_inizio
# $.[].ora_fine
# $.[].data
# $.[].tipo
# $.[].display[]
# $.[].{$.[].display.}
# $.[].insegnamento_tipo[]
# $.celle.*.tipo
# $.[].docente
# $.[].nome_insegnamento
# $.[].codice_aula