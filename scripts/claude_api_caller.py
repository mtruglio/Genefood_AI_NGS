import anthropic
import json
import re

def ask_claude(json_file, prompt, analysis_type):
    mod = "claude-sonnet-4-5-20250929"
    headers = {}
    
    with open(json_file, 'r') as file:
        json_content = json.load(file)
    print("JSON LOADED")
    
    json_string = json.dumps(json_content)
    print(f"JSON string length: {len(json_string)} characters")
    
    client = anthropic.Anthropic(
        api_key="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",
    )
    
    system_prompt = f"Sei un esperto dietologo. Sei parte di un servizio che costruisce piani nutrizionali in base al profilo genetico delle persone. Il file json seguente e' la tua esperienza, basata su decine di casi passati. Il formato in cui sono scritte le indicazioni e' lo stesso che userai per generarne di nuove (json). Puoi aggiungere alimenti a tua discrezione, ma sempre attenendoti strettamente alle condizioni del paziente che ti indico. Non inferire condizioni non esplicitamente fornite (ad esempio intolleranze laddove non sono specificate). Se possibile, cerca il caso piu' vicino al paziente nel json che hai memorizzato, e parti da li' per fare le necessarie modifiche. A questo scopo, puoi valutare la \"vicinanza\" basandoti sulle condizioni presenti nel campo \"condizioni\" in ogni record nel JSON. Per creare la sezione \"Diagnosi\", attingi alle diagnosi molto dettagliate che trovi nei record del JSON, combinandole in maniera sensata in un testo esteso e altrettanto dettagliato. Ricorda: intolleranza al glutine non implica automaticamente intolleranza al lattosio, a meno che non sia esplicitamente scritto nel profilo paziente. Dopo aver generato il piano nutrizionale, accertati che non ci siano contraddizioni (ad esempio lo stesso alimento tra i Consigliati, Tollerati e Sconsigliati), e in caso risolvile. Il file JSON:<data>{json_string}</data>"
    
    try:
        full_response = ""
        
        # Create a streaming message
        with client.messages.stream(
            model=mod,
            max_tokens=16000,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            extra_headers=headers
        ) as stream:
            print("Streaming started...")
            
            # IMPORTANTE: raccogli TUTTO lo stream prima di uscire dal context manager
            for text in stream.text_stream:
                full_response += text
                if len(full_response) % 100 == 0:
                    print(f"Received {len(full_response)} characters so far...")
        
        # Ora siamo FUORI dal context manager, lo stream è completo
        print(f"\nTotal response length: {len(full_response)} characters")
        
        if not full_response:
            print("WARNING: Empty response received from Claude!")
            return None
        
        # Mostra i primi 500 caratteri per debug
        print(f"Response preview: {full_response[:500]}...")
        
        # Clean the response
        try:
            cleaned_response = clean_json_response(full_response)
            print(f"Cleaned response length: {len(str(cleaned_response))} characters")
            return cleaned_response
        except Exception as clean_error:
            print(f"ERROR in clean_json_response: {clean_error}")
            print(f"Returning raw response instead")
            # Ritorna la risposta raw se clean fallisce
            return full_response
            
    except anthropic.APIError as e:
        print(f"API Error: {e}")
        print(f"Status code: {e.status_code}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None
    
def clean_json_response(response):
    """
    Clean the response by removing markdown code block delimiters
    and ensuring it's valid JSON.
    """
    # Remove ```json at the beginning if present
    response = re.sub(r'^```json\s*', '', response.strip())
    
    # Remove ``` at the end if present
    response = re.sub(r'\s*```$', '', response.strip())
    
    # Remove any other markdown code block markers that might be present
    response = re.sub(r'```\w*\s*', '', response)
    response = re.sub(r'\s*```', '', response)
    
    # Validate that we can parse it as JSON
    try:
        # Parse and re-serialize to ensure it's valid JSON
        parsed_json = json.loads(response)
        return json.dumps(parsed_json, ensure_ascii=False, indent=2)
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse response as JSON: {e}")
        # Return the cleaned string anyway
        return response