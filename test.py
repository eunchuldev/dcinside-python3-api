import asyncio
import dc_api

async def run():
    api = await dc_api.API().open()
    async for metadoc in api.board(board_id='aoegame'):
        print(metadoc)
        async for comm in metadoc.comments:
            print(comm)
    #doc_id = await api.write_document(board_id="programming", title="java vs python", contents="닥치고 자바", name="ㅇㅇ", password="1234")
    await api.close()

asyncio.get_event_loop().run_until_complete(run())
