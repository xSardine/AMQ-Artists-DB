Help()
{
   # Display Help
   echo "Process the data in expand.json and do the mapping"
   echo
   echo "Syntax: start_service.sh [-p|-a|-g|-h]"
   echo "options:"
   echo "p     ignore the processing of the data not in expand (if already done)"
   echo "a     ignore the mapping of artists"
   echo "g     ignore the mapping of groups"
   echo "h     Show this help panel"
   echo
}

flag_ignore_preprocess_data=false
flag_ignore_artist_mapping=false
flag_ignore_group_mapping=false

while [ -n "$1" ]; do # while loop starts

	case "$1" in

    -p) flag_ignore_preprocess_data=true ;;

	-a) flag_ignore_artist_mapping=true ;;

    -g) flag_ignore_group_mapping=true ;;

    -h) Help 
        exit;;

	*) echo "Option $1 not recognized, use option -h to see available options" 
       exit;;

	esac

	shift

done

if $flag_ignore_preprocess_data; then
    echo "Ignoring preprocessing of data"
else
    python preprocess_data.py
fi

if $flag_ignore_artist_mapping; then
    echo "Ignoring mapping of artists"
else
    python map_artist_id.py
fi

if $flag_ignore_group_mapping; then
    echo "Ignoring mapping of groups"
else
    python map_group_id.py
fi
