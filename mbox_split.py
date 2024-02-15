#!/usr/bin/env python3

import argparse
import mailbox
import os
import sys
from email.header import decode_header
from email.errors import HeaderParseError

def decode_rfc2822(header_value):
    """Decodes and returns the value of a rfc2822 encoded header.
    
    Args:
        header_value (str): The header value to decode.

    Returns:
        str: The decoded header value.
    """
    result = []
    for binary_value, charset in decode_header(header_value):
        if isinstance(binary_value, str):
            result.append(binary_value)
            continue

        decoded_value = None
        if charset:
            try:
                decoded_value = binary_value.decode(charset, errors='ignore')
            except Exception as e:
                print(f"Error decoding header: {e}")

        if decoded_value is None:
            try:
                decoded_value = binary_value.decode('utf8', errors='ignore')
            except Exception as e:
                decoded_value = f'HEX({binary_value.hex()})'

        result.append(decoded_value)

    return ''.join(result)

def process_mbox(infile, prefix):
    """Processes the mbox file and splits it into separate mbox files based on Gmail labels.

    Args:
        infile (str): Path to the input mbox file.
        prefix (str): Prefix for the output mbox files.
    """
    boxes = {
        "inbox": mailbox.mbox(f"{prefix}Inbox.mbox", None, True),
        "sent": mailbox.mbox(f"{prefix}Sent.mbox", None, True),
        "archive": mailbox.mbox(f"{prefix}Archive.mbox", None, True),
    }

    for message in mailbox.mbox(infile):
        target = "archive"
        gmail_labels = message.get("X-Gmail-Labels", "").lower()
        if gmail_labels:
            gmail_labels = decode_rfc2822(gmail_labels)

        if "inbox" in gmail_labels:
            target = "inbox"
        elif "sent" in gmail_labels:
            target = "sent"
        else:
            for label in gmail_labels.split(','):
                if label not in ["important", "unread", "starred", "newsletters"]:
                    target = f"{prefix}{label.title().replace(os.pathsep, '.')}.mbox"
                    if target not in boxes:
                        boxes[target] = mailbox.mbox(target, None, True)
                    break
        try:
            boxes[target].add(message)
        except HeaderParseError as e:
            print(f"HeaderParseError: {e} - Message skipped.")

def main():
    """Main function to execute the script."""
    parser = argparse.ArgumentParser(description="Split a Gmail Mbox into multiple Mbox files based on labels.")
    parser.add_argument("-i", "--infile", required=True, help="Input mbox file.")
    parser.add_argument("-p", "--prefix", default="split_", help="Prefix for output mbox files.")
    args = parser.parse_args()

    print(f"Processing file - {args.infile} with prefix = {args.prefix}")
    process_mbox(args.infile, args.prefix)

if __name__ == "__main__":
    main()
