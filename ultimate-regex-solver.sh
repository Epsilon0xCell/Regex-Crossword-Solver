#!/bin/bash

# I treat this file as a menu, not as one program. Options 1, 3, and 4
# download an outside project and run it where it lands. Only option 2
# runs code from this repo, and it needs ply and z3-solver installed
# first. The other options can work while option 2 cannot, and the
# other way around.

# Presented on replit, remove sudo statements if needed

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

# Two warnings I keep in mind when I run this. The options use sudo
# rm -rf on the download folder before cloning, so a rerun clears the
# old copy instead of failing on it, and I never run this in a folder
# that holds work I care about. And option 1 runs python2 because that
# downloaded project is Python 2 era code, while my bundled solver in
# option 2 is Python 3.
PS3='Please choose an option: '
select opt in "${options[@]}"; do
    case $opt in
        "MIT Mystery Hunt Challenge Solver rated the hardest Regex Crossword Challenge to solve in the world")
            echo "You selected Solve MIT Mystery Hunt Regex Challenge"
            sudo rm -rf regex-crossword
            git clone https://github.com/dneiter/regex-crossword.git
            cd regex-crossword
            python2 main.py
            break
            ;;
        "Solve the BBC Radio 4 Regex Puzzle, this is a hard level difficulty challenge")
            echo "You have selected to solve the BBC Radio 4 Regex Puzzle"
            sudo pip install ply z3-solver
            sudo python3 custom-solver.py
            break
            ;;
        "Download Directory Of Solutions All Levels make sure to grep the file use this if you don't have much time or don't know programming")
            echo "You selected to download the largest directory of solutions for the regex crossword challenges make sure to grep the solution to find what you are looking for faster"
            sudo rm -rf RegexCrossword
            git clone https://github.com/deepaksood619/RegexCrossword.git
            cd RegexCrossword
            ls
            cat README.md
            break
            ;;
        "Download custom regex solver that can be modified by editing the source code to solve even a challenge with backlinks, this converts the problem into a SMT problem and then Z3PY to solve it use this if you have a lot of time and know programming to create your own custom regex solver this is also perfect for solving rectangular challenges")
            echo "You opted to download a custom regex solver that can solve pretty much any challenge if you modify the source code to do so"
            pip install ply z3-solver
            sudo rm -rf regex-crossword-solver
            git clone https://github.com/blukat29/regex-crossword-solver.git
            cd regex-crossword-solver
            ls
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
