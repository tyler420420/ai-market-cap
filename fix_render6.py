path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the start of the row rendering in renderTable
# Looking for: html+='<tr style="background:'+bg+'"><td>...
idx = content.find("html+='<tr style")
print(f"html+='<tr style found at: {idx}")
if idx >= 0:
    segment = content[idx:idx+50]
    print(f"First 50 chars (raw): {segment}")
    print(f"First 50 chars (repr): {repr(segment)}")
    # Try to find the end
    end = content.find("sortBy('days_left');", idx)
    if end >= 0:
        end += len("sortBy('days_left');")
        full = content[idx:end]
        print(f"Full segment length: {len(full)}")
        # Now let's do the replacement
        old = segment  # We'll just replace the beginning
        new = segment.replace("'<tr style=\"background:'+bg+'\"'><td><strong><a href=\"https://finance.yahoo.com/quote/'+r.ticker+'\" target=\"_blank\" style=\"color:#66b2ff\">'+r.ticker+'</a></strong></td>';html+='<td>'+r.company_name", "'<tr style=\"background:'+bg+'\"'><td data-label=\"Ticker\"><strong><a href=\"https://finance.yahoo.com/quote/'+r.ticker+'\" target=\"_blank\" style=\"color:#66b2ff\">'+r.ticker+'</a></strong></td>';html+='<td data-label=\"Company\">'+r.company_name")
        if new != segment:
            print("REPLACEMENT WORKS")
            # Do the full replacement
            content2 = content.replace(old, new, 1)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content2)
            print("Written")
        else:
            print("No change - pattern not found")
            # Show what the actual beginning looks like
            print(f"Actual beginning: {repr(segment[:120])}")