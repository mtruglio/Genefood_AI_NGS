import anthropic
import json

def ask_claude(json_file, prompt):
    with open(json_file, 'r') as file:
        json_content = json.load(file)
    print("JSON LOADED")
    # Convert the JSON content back to a string
    json_string = json.dumps(json_content)
    client = anthropic.Anthropic(
        # defaults to os.environ.get("ANTHROPIC_API_KEY")
        api_key="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",
    )
    message = client.messages.create(
    model="claude-3-5-sonnet-20240620",
    max_tokens=8192,
    temperature=0.2,
    system=f"Sei un esperto dietologo. Sei parte di un servizio che costruisce piani nutrizionali in base al profilo genetico delle persone. Il file json seguente e' la tua esperienza, basata su decine di casi passati. Il formato in cui sono scritte le indicazioni e' lo stesso che userai per generarne di nuove (json). Puoi aggiungere alimenti a tua discrezione, ma sempre attenendoti strettamente alle condizioni del paziente che ti indico. Non inferire condizioni non esplicitamente fornite (ad esempio intolleranze laddove non sono specificate). Se possibile, cerca il caso piu' vicino al paziente nel json che hai memorizzato, e parti da li' per fare le necessarie modifiche. A questo scopo, puoi valutare la \"vicinanza\" basandoti sulle condizioni presenti nel campo \"condizioni\" in ogni record nel JSON. Per creare la sezione \"Diagnosi\", attingi alle diagnosi molto dettagliate che trovi nei record del JSON, combinandole in maniera sensata in un testo esteso e altrettanto dettagliato.Ricorda: intolleranza al glutine non implica automaticamente intolleranza al lattosio, a meno che non sia esplicitamente scritto nel profilo paziente. Dopo aver generato il piano nutrizionale, accertati che non ci siano contraddizioni (ad esempio lo stesso alimento tra i Consigliati, Tollerati e Sconsigliati), e in caso risolvile. Ora leggi il json, imparalo, non fare altro e aspetta una mia richiesta.Il file JSON:<data>{json_string}</data>",
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
    extra_headers={
        "anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"
    }
    )
    return message.content


