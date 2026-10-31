#!/bin/bash

# I treat this file as a menu, not as one program. Options 1, 3, and 4
# download an outside project at one pinned commit, show its file
# list, and stop. Nothing in those options runs the downloaded code.
# Only option 2 runs code, the bundled solver from this repo, and it
# needs ply and z3-solver installed first. No option in this menu
# runs with raised privileges, and no option deletes a download
# folder that is already here: if the folder exists, the option
# stops and says so.

# Run from the folder this script lives in, so custom-solver.py is found
# no matter where the script is launched from.
cd "$(dirname "$0")" || exit 1

# If you want to solve official challenges you can either review notes or modify the custom solver

text="Epsilon0xCell"
colors=("\033[31m" "\033[33m" "\033[32m" "\033[36m" "\033[34m" "\033[35m")

explosions=("💥" "💥" "🔥" "💥" "💣" "💥" "💥" "🔥")

for ((i=0;i<${#text};i++)); do
  color=${colors[$((i%${#colors[@]}))]}
  explosion=${explosions[$((i%${#explosions[@]}))]}
  echo -en "${color}${text:$i:1} ${explosion}\033[0m"
  sleep 0.4
done
echo

options=(
    "MIT Mystery Hunt Challenge Solver rated the hardest Regex Crossword Challenge to solve in the world"
    "Solve the BBC Radio 4 Regex Puzzle, this is a hard level difficulty challenge"
    "Download Directory Of Solutions All Levels make sure to grep the file use this if you don't have much time or don't know programming"
    "Download custom regex solver that can be modified by editing the source code to solve even a challenge with backlinks, this converts the problem into a SMT problem and then Z3PY to solve it use this if you have a lot of time and know programming to create your own custom regex solver this is also perfect for solving rectangular challenges"
    "Quit"
)

# The pinned commits below are the upstream default branch heads
# I recorded when I changed this menu. A clone checks out exactly
# that commit, so what lands on disk does not drift with upstream.
# Option 1 used to run its download at once with python2. That
# project is Python 2 era code. This menu now leaves running it
# as a manual step for whoever wants to read it first.
PIN_DNEITER="a8f38a5f96863a6799dfc9697b6ace851cdcb90e"
PIN_DEEPAK="020374dcf1bd51091224a057d09b48412af1e263"
PIN_BLUKAT="a8591dea3438a58271f39bfbc9cddf7de0f079de"

clone_pinned() {
    clone_dir="$1"
    clone_url="$2"
    clone_commit="$3"
    if [ -e "$clone_dir" ]; then
        echo "A folder named $clone_dir already exists here."
        echo "I did not delete it or write over it. Move it aside yourself, then choose this option again."
        return 1
    fi
    git clone "$clone_url" || return 1
    cd "$clone_dir" || return 1
    git checkout "$clone_commit" || return 1
    echo "Cloned $clone_url at commit $clone_commit."
    ls
}
PS3='Please choose an option: '
select opt in "${options[@]}"; do
    case $opt in
        "MIT Mystery Hunt Challenge Solver rated the hardest Regex Crossword Challenge to solve in the world")
            echo "You selected Solve MIT Mystery Hunt Regex Challenge"
            if clone_pinned "regex-crossword" "https://github.com/dneiter/regex-crossword.git" "$PIN_DNEITER"; then
                if [ -f README.md ]; then
                    cat README.md
                fi
                echo "Stopped here on purpose. I did not run this project."
                echo "It is Python 2 era code. Read it first, and if you still want to run it, run python2 main.py from this folder yourself."
            fi
            break
            ;;
        "Solve the BBC Radio 4 Regex Puzzle, this is a hard level difficulty challenge")
            echo "You have selected to solve the BBC Radio 4 Regex Puzzle"
            python3 -m pip install ply z3-solver
            python3 custom-solver.py
            break
            ;;
        "Download Directory Of Solutions All Levels make sure to grep the file use this if you don't have much time or don't know programming")
            echo "You selected to download the largest directory of solutions for the regex crossword challenges make sure to grep the solution to find what you are looking for faster"
            if clone_pinned "RegexCrossword" "https://github.com/deepaksood619/RegexCrossword.git" "$PIN_DEEPAK"; then
                if [ -f README.md ]; then
                    cat README.md
                fi
            fi
            break
            ;;
        "Download custom regex solver that can be modified by editing the source code to solve even a challenge with backlinks, this converts the problem into a SMT problem and then Z3PY to solve it use this if you have a lot of time and know programming to create your own custom regex solver this is also perfect for solving rectangular challenges")
            echo "You opted to download a custom regex solver that can solve pretty much any challenge if you modify the source code to do so"
            python3 -m pip install ply z3-solver
            clone_pinned "regex-crossword-solver" "https://github.com/blukat29/regex-crossword-solver.git" "$PIN_BLUKAT"
            break
            ;;
        "Quit")
            echo "Goodbye!"
            break
            ;;
        *)
            echo "Invalid option, try again"
            ;;
    esac
done
