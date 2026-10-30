def generate_recommendation_message(customer_name, products):
    if not products:
        return (
            f"Welcome back, {customer_name}. "
            "I couldn't find a new recommendation for you right now."
        )

    product = products[0]

    return (
        f"Welcome back, {customer_name}! "
        f"I found something you might love. "
        f"Our {product.name} is currently available in our collection. "
        f"I think it could be a beautiful addition to your jewellery collection."
    )