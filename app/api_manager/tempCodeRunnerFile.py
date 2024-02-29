    if data is None:
            raise ValueError("Data cannot be None")
        
        chunk_size = 4096  # Adjust chunk size as needed
        yield "[\n"
        for index, item in enumerate(data):
            if item is not None:
                item_str = json.dumps({"product_name": item["product_name"], "lowest_prices": item["lowest_prices"]})
                for i in range(0, len(item_str.encode('utf-8')), chunk_size):
                    yield "  " + item_str[i:i + chunk_size] + ("\n" if index < len(data) - 1 else "")  # Add comma unless it's the last element
        yield "]"