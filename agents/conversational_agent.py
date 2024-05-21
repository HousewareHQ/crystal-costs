from db.snowflake import Snowflake

prompt_initial = """
###
            You are a Cost Monitoring tool for data warehouses like Snowflake, designed to ease the effort of developers. Your primary responsibilities include
            answering users' questions. If the user seems to be asking to get the credits consumed, or the cost of a query, or predicting use of credits, you should
            "Looking up data for this". 
            Remember to exactly reply with this sentence only - "Looking up data for this". 
            It must be present in your output.
            You have context of previous messages. If user has asked for a summary of the previous message, you don't need to look up data for that.
            If the user is asking a question that does not require looking up data, then simply reply by answering their question based on the context of the messages till now.
            CONVERSATION IS GIVEN BELOW THIS
            ###
        """



def convert_into_snowflake_messages(messages):
    converted_messages = [
        {'role': 'system', 'content': prompt_initial}
    ]
    for message in messages:
        content = message.content
        content = content.replace("'", "")
        if message is not None and message.type == 'ai':
            converted_messages.append({'role': 'assistant', 'content': content})
        else:
            converted_messages.append({'role': 'user', 'content': content})
    return converted_messages


def get_snowflake_arctic_results(messages, sf) -> str:
    converted_to_sf_messages = convert_into_snowflake_messages( messages)
    pred = sf.call_arctic_complete(converted_to_sf_messages)
    return pred

