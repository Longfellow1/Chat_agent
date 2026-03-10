"""

This example describes how to use the workflow interface to stream chat.

"""



import os

\# Our official coze sdk for Python \[cozepy](https://github.com/coze-dev/coze-py)

from cozepy import COZE\_CN\_BASE\_URL



\# Get an access\_token through personal access token or oauth.

coze\_api\_token = '**cztei\_hGcB7WGP1H6IcnSRgymPU3RxTrvxKG5fPN1mMJ66VElvm6LSCdAE9VZ2LDBSNH40r**'

\# The default access is api.coze.com, but if you need to access api.coze.cn,

\# please use base\_url to configure the api endpoint to access

coze\_api\_base = COZE\_CN\_BASE\_URL



from cozepy import Coze, TokenAuth, Stream, WorkflowEvent, WorkflowEventType  # noqa



\# Init the Coze client through the access\_token.

coze = Coze(auth=TokenAuth(token=coze\_api\_token), base\_url=coze\_api\_base)



\# Create a workflow instance in Coze, copy the last number from the web link as the workflow's ID.

workflow\_id = '**7611375200538771491**'





\# The stream interface will return an iterator of WorkflowEvent. Developers should iterate

\# through this iterator to obtain WorkflowEvent and handle them separately according to

\# the type of WorkflowEvent.

def handle\_workflow\_iterator(stream: Stream\[WorkflowEvent]):

&nbsp;   for event in stream:

&nbsp;       if event.event == WorkflowEventType.MESSAGE:

&nbsp;           print("got message", event.message)

&nbsp;       elif event.event == WorkflowEventType.ERROR:

&nbsp;           print("got error", event.error)

&nbsp;       elif event.event == WorkflowEventType.INTERRUPT:

&nbsp;           handle\_workflow\_iterator(

&nbsp;               coze.workflows.runs.resume(

&nbsp;                   workflow\_id=workflow\_id,

&nbsp;                   event\_id=event.interrupt.interrupt\_data.event\_id,

&nbsp;                   resume\_data="hey",

&nbsp;                   interrupt\_type=event.interrupt.interrupt\_data.type,

&nbsp;               )

&nbsp;           )





handle\_workflow\_iterator(

&nbsp;   coze.workflows.runs.stream(

&nbsp;       workflow\_id=workflow\_id,

&nbsp;   )

)







curl -X POST '**https://api.coze.cn/v1/workflow/stream\_run**' \\

-H "Authorization: **Bearer cztei\_hGcB7WGP1H6IcnSRgymPU3RxTrvxKG5fPN1mMJ66VElvm6LSCdAE9VZ2LDBSNH40r**" \\

-H "Content-Type: application/json" \\

-d '{

&nbsp; "workflow\_id": "**7611375200538771491**",

&nbsp; "parameters": {

&nbsp;   "CONVERSATION\_NAME": "Default",

&nbsp;   "USER\_INPUT": "你知道我叫什么名字吗"

&nbsp; }

}'





