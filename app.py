import argparse
import requests
from queue import Queue

def test_domain(domain):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        # proper requesting sending with waiting upto 5 seconds and checking the response
        response = requests.get(domain, headers=headers, timeout=15)
        print("Initial response: ", response.status_code, "for", domain)
        if response.status_code == 200:
            print(" Response is 200 OK")
            return True
            # check the domain has http or https
        elif not domain.startswith("http://") and not domain.startswith("https://"):
            domain = "http://" + domain
            print("Trying with the", domain)
            response = requests.get(domain, timeout=15)
            if response.status_code == 200:
                return True
            else:
                return False
        elif domain.startswith("http://"):
                domain = domain.replace("http://", "https://")
                print("Trying with the", domain)
                response = requests.get(domain, timeout=15)
                if response.status_code == 200:
                    return True
                else:
                    return False
        elif domain.startswith("https://"):
            domain = domain.replace("https://", "http://")
            print("Trying with the", domain)
            response = requests.get(domain, timeout=15)
            if response.status_code == 200:
                return True
            else:
                return False
        elif response.status_code in [301, 302]:
            print("Redirecting to", response.headers["Location"])
            redirect_url = response.headers["Location"]
            response = requests.get(redirect_url, timeout=15)
            if response.status_code == 200:
                return True
            else:
                return False
        else:
            return False
    except requests.exceptions.RequestException as e:
        return False

def load_domain_list(domain_list):
    with open(domain_list, "r") as file:
        # assign domain and categories to a list
        domain_list = file.readlines()
        domain_list = [domain.strip() for domain in domain_list]
    return domain_list

def categorize_domains(domain_list, categories=None, gtld_types=None):
    domain_queue = Queue()

    categorized_domains = {}
    for domain in domain_list:
        # separate domain and category
        domain, category = domain.split(" ")
        if category in categorized_domains:
            categorized_domains[category].append(domain)
        else:
            categorized_domains[category] = [domain]
    
    if categories:
        for category in categorized_domains:
            if gtld_types:
                for domain in categorized_domains[category]:
                    for gtld_type in gtld_types:
                        if domain.endswith(gtld_type):
                            domain_queue.put(domain)
                        else:
                            # remove all the domains that are not in the specified gtld types from the categorized domains dictionary
                            categorized_domains[category].remove(domain)
            else:
                for domain in categorized_domains[category]:
                    domain_queue.put(domain)
        # remove all the categories from dictionary that are not in the specified categories
        for category in list(categorized_domains.keys()):
            if category not in categories:
                del categorized_domains[category]
    else:
        # put all the categorized domains into the domain queue
        print("No categories specified. Checking all domains.")
        for domains in categorized_domains.values():
            if gtld_types:
                for domain in domains:
                    for gtld_type in gtld_types:
                        if domain.endswith(gtld_type):
                            domain_queue.put(domain)
            else:
                for domain in domains:
                    domain_queue.put(domain)
    
    return categorized_domains, domain_queue
    


    
def main(domain_list, categories, gtld_types,  output_file=None):


    results = {}
    domains = load_domain_list(domain_list)

    categorized_domains, domain_queue = categorize_domains(domains, categories, gtld_types)

    # domain testing loop
    while domain_queue and not domain_queue.empty():
        domain = domain_queue.get()
        result = test_domain(domain)
        results[domain] = result
        print(f"Domain: {domain} - Result: {result}")
    
    if output_file:
        with open(args.output_file, "w") as file:
            # write into file according to the category
            for category, category_domains in categorized_domains.items():
                file.write(f"Category: {category}\n")
                for domain in category_domains:
                    file.write(f"Domain: {domain} - Result: {results[domain]}\n")
                file.write("\n")
    return results
    # print(results)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Security tool for checking allowed domains in the network.")
    parser.add_argument("--domain-list", help="Path to the domain list file.", required=False)
    parser.add_argument("--categories", nargs="+", help="Domain categories to check for.", required=False)
    parser.add_argument("--gtld-types", nargs="+", help="Domain GTLD types to check for.", required=False)
    parser.add_argument("--output-file", help="Path to the output file.", required=False)
    args = parser.parse_args()

    main(args.domain_list, args.categories, args.gtld_types, args.output_file)
