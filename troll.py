import asyncio
from pyrogram import Client
import config
from motor.motor_asyncio import AsyncIOMotorClient

async def inject_session():
    print("🚀 String Session Setup Started...")
    print("Terminal mein apna Phone Number aur OTP daalna (Bot bypass ho raha hai)\n")
    
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
    
    # Direct MongoDB connection (bina kisi file ko import kiye)
    db_client = AsyncIOMotorClient(config.MONGO_URI)
    db = db_client[config.DB_NAME]
    
    # Direct inject string session into 'bot_config' collection
    await db["bot_config"].update_one(
        {"key": "string_session"},
        {"$set": {"key": "string_session", "value": session_string}},
        upsert=True
    )
    
    print("🎉 Injection Successful! Ab bot ko start kar de, wo direct DB se session utha lega.")
    await app.stop()

if __name__ == "__main__":
    asyncio.run(inject_session())

