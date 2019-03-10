MYDOT_COMPLETE="\
    add\
    commit\
    init\
    pull\
    push\
    remove\
    status\
	list\
    --path\
    --loglevel\
    --help"

MYDOT_LOGLEVEL_COMPLETE="\
    DEBUG\
    INFO\
    WARNING\
    ERROR\
    CRITICAL\
    NOTSET"

MYDOT_COMMIT_COMPLETE="\
    --message\
    --help"

MYDOT_STATUS_COMPLETE="\
	--silent\
	--help"


_mydot_complete()
{
	local cur prev firstword suggestions
	cur="${COMP_WORDS[COMP_CWORD]}"
	prev="${COMP_WORDS[COMP_CWORD-1]}"
	firstword=$(_mydot_get_firstword)

	case "${firstword}" in
		add)
			compopt -o default
			COMPREPLY=()
			return 0
			;;
		commit)
			suggestions="$MYDOT_COMMIT_COMPLETE"
			;;
		status)
			suggestions="$MYDOT_STATUS_COMLPETE"
			;;
		*)
			case "${prev}" in
				--loglevel)
					suggestions="$MYDOT_LOGLEVEL_COMPLETE"
					;;
				*)
					suggestions="$MYDOT_COMPLETE"
					;;
			esac
			;;
	esac

	if [[ "${suggestions}x" == "x" ]];then
		COMPREPLY=()
	else
		COMPREPLY=( $(compgen -W "${suggestions}" -- ${cur}) )
	fi
	return 0
}

_mydot_get_firstword() {
	local firstword i

	firstword=
	for ((i = 1; i < ${#COMP_WORDS[@]}; ++i)); do
		if [[ ${COMP_WORDS[i]} != -* ]]; then
			firstword=${COMP_WORDS[i]}
			break
		fi
	done
	echo $firstword
}

complete -F _mydot_complete mydot

