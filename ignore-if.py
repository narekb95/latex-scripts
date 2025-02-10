# TODO
# 1. delete whole line if an if aline
# 2. make command line arguments
# 3. allow multiple ignore conditions at once
# 4. handle comment environment
# 5. delete newif and longrue longfalse
# 6. handle nested ifs
# 7. add command line argument to delete comments


import re



def handle_output(line, curr_pos, match, stack, condition, outfile):
    command_pos = match.start() if match else None
    prefix = line[curr_pos:command_pos]
    outfile.write(prefix)
    if not match:
        return
    if (match.group(0)).startswith('\\if') and match.group(1) != condition \
        or match.group(0) == '\\else' and stack[-1][0] != condition \
        or match.group(0) == '\\fi' and stack[-1][0] != condition:
            outfile.write(match.group(0))


def reduce_comment(line):
    # Remove comments from line
    comment = re.match(r'(?<!\\)%.*', line)
    if comment:
        pos = comment.start()
        comment = line[pos:]
        line = line[:pos]
    else:
        comment = ''
    return (line, comment)

def process_latex_file(input_filename, output_filename, condition, ignore_if):
    # Stack to keep track of \ifword conditions
    ignore_count = 0  # Counter to track nested \if{condition}

    defined_ifs = set()

    # Regular expressions
    newif_pattern = re.compile(r'\\newif\\if(\w+)')



    with open(input_filename, 'r', encoding='utf-8') as infile, open(output_filename, 'w', encoding='utf-8') as outfile:

        stack = []
        for line in infile:
            (line, comment) = reduce_comment(line)

            newif_match = newif_pattern.search(line)
            if newif_match:
                defined_ifs.add(newif_match.group(1))                
                if ignore_count == 0:
                    outfile.write(line+comment)
                continue
            
            # get all matches of if{condition}, else, fi using matchall
            all_matches = re.finditer(r'\\if(\w+)|\\else|\\fi', line)
            curr_match = next(all_matches, None)
            start_pos = 0

            while curr_match:
                if ignore_count == 0:
                    handle_output(line, start_pos, curr_match, stack, condition, outfile)
                    
                if curr_match.group(0).startswith('\\if') \
                    and curr_match.group(1) in defined_ifs:
                    stack.append((curr_match.group(1), "if"))
                    if curr_match.group(1) == condition:
                        if ignore_if:
                            ignore_count += 1
                elif curr_match.group(0) == '\\else':
                    top_if, _ = stack.pop()
                    stack.append((top_if, "else"))
                    if top_if == condition:
                        if not ignore_if:
                            ignore_count += 1
                        else:
                            ignore_count -= 1
                elif curr_match.group(0) == '\\fi':
                    top_if, state = stack.pop()
                    if top_if == condition and \
                        ((ignore_if and state == "if" )
                         or (not ignore_if and state == "else")):
                        ignore_count -= 1
                        
                start_pos = curr_match.end()
                curr_match = next(all_matches, None)

            if ignore_count == 0:
                # print rest and comment
                outfile.write(line[start_pos:] + comment)


# Example usage
input_filename = "main.tex"  # Replace with the actual LaTeX file
output_filename = "output.tex"
condition = "short"  # Replace with the desired condition to ignore
ignore_if = True  # Set to False to ignore \else instead of \if
process_latex_file(input_filename, output_filename, condition, ignore_if)


input_filename = "output.tex"  # Replace with the actual LaTeX file
output_filename = "output2.tex"
condition = "long"  # Replace with the desired condition to ignore
ignore_if = False  # Set to False to ignore \else instead of \if
process_latex_file(input_filename, output_filename, condition, ignore_if)
