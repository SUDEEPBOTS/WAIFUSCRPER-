import asyncio
from pyrogram import Client
import config
from WAIFUSCRPER.Database.MongoDB import set_string_session

async def inject_session():
    print("🚀 String Session Setup Started...")
    print("Terminal mein apna Phone Number aur OTP daalna (Bot bypass ho raha hai)\n")
    
    # In-memory client banayenge taaki file save na ho, sirf string mile
    app = Client(
        "inject_session", 
        api_id=config.API_ID, 
        api_hash=config.API_HASH, 
        in_memory=True
    )
    
    await app.start()
    session_string = await app.export_session_string()
    
    print("\n✅ Session String ban gaya!")
    print("💉 MongoDB mein inject kar raha hu...")
    
    # Teri file ka function use karke DB me dal diya
    await set_string_session(session_string)
    
    print("🎉 Injection Successful! Ab bot ko start kar de, wo direct DB se session utha lega.")
    await app.stop()

if __name__ == "__main__":
    asyncio.run(inject_session())
