import dotenv 
import os 

from handlers import groups

dotenv.load_dotenv()


print(groups.get_groups(os.environ["ORG_ID"]))