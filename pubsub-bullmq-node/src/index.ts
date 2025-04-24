import express from 'express';
import dragonflyClient from './utils/dragonflyClient';
import { DragonflyPublisher } from './pubsub/pub';
import { DragonflySubscriber } from './pubsub/sub';

// The Express application.
const app = express();
app.use(express.json());

// Pub/Sub.
const dragonflySubscriberMessagerHandler = (channel: string, message: string) => {
    console.log(`processing message: ${message}`);
};
const dragonflyPublisher = new DragonflyPublisher(dragonflyClient.dragonfly, 'my-channel');
const dragonflySubscriber = new DragonflySubscriber(dragonflyClient.dragonflySubscriber, 'my-channel', dragonflySubscriberMessagerHandler);

app.post('/pub-sub-message', (req, res) => {
    dragonflyPublisher.publish(JSON.stringify(req.body));
    res.json({ message: 'successfully procssed message' })
})

// Start the server.
const PORT = 3000
app.listen(PORT, () => {
    console.log(`server is running on http://localhost:${PORT}`)
})
