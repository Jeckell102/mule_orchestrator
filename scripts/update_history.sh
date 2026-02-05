Bash
# Append these to your ~/.bashrc if they aren't there, or update existing ones
sed -i 's/^HISTSIZE=.*/HISTSIZE=10000/' ~/.bashrc
sed -i 's/^HISTFILESIZE=.*/HISTFILESIZE=20000/' ~/.bashrc
source ~/.bashrc