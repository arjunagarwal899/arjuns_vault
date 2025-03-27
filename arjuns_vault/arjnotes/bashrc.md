```bash
# ---------- TERMINAL COLOUR PROFILE ----------
# Force color prompt
force_color_prompt=yes

# Check if color support is available
if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
        # Terminal supports colors, enable color prompt
        color_prompt=yes
    else
        color_prompt=
    fi
fi

# Set up the shell prompt (PS1) with colors if supported
if [ "$color_prompt" = yes ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi

# Clean up environment variables to avoid pollution
unset color_prompt force_color_prompt

# If using xterm or rxvt, set the terminal title
case "$TERM" in
    xterm*|rxvt*)
        PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
        ;;
    *)
        ;;
esac

# Enable color support for ls, grep, and related commands
if [ -x /usr/bin/dircolors ]; then
    # Load color configuration from ~/.dircolors if available, else use defaults
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    
    # Define aliases for colorized output
    alias ls='ls --color=auto'
    # alias dir='dir --color=auto'  # Uncomment if needed
    # alias vdir='vdir --color=auto'  # Uncomment if needed
    
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# Enable colored output for GCC warnings and errors
export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'


# ---------- ALIASES AND VARIABLES ----------
alias pip=pip3
alias python=python3
alias nv=nvidia-smi
alias rp=realpath
alias c="clear"
alias l="ls -alh"
alias cl="c; l"
alias wfc="watch -n1 'ls -1 | wc -l'"
alias wl="watch -n1 'ls -lah'"
alias wnv="watch -n1 nvidia-smi"
alias nvi="nvitop -1"
alias wnvi="nvitop"
alias wt="watch -n1 tree"
alias wtc="watch -n1 'tree | wc -l'"
alias jl="jupyter lab --port "
alias pid="ps -aux | grep "

export PATH="$HOME/projects/bin:$PATH"
export PATH="$HOME/projects/arjuns_vault/arjuns_vault/arjbun:$PATH"
```