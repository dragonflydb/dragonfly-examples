import express from 'express';
import { DragonflyPublisher } from './pubsub/pub';
import { DragonflySubscriber } from './pubsub/sub';

// Express application.
const app = express();
app.use(express.json());

// Dragonfly native Pub/Sub messaging.
const pubsubChannel = 'my-pub-sub-channel';
const pubsubMessagerHandler = async (channel: string, message: string) => {
    await new Promise(resolve => setTimeout(resolve, 2000));
    console.log(`Pub/Sub message processed: ${message}`);
};
const dragonflyPub = new DragonflyPublisher(pubsubChannel);
const dragonflySub = new DragonflySubscriber(pubsubChannel, pubsubMessagerHandler);

// Express handlers.
app.post('/pub-sub-message', (req, res) => {
    dragonflyPub.publish(JSON.stringify(req.body));
    res.json({ message: 'Pub/Sub message received' });
});

// Server initialization.
const PORT = parseInt(process.env.DRAGONFLY_PORT || '3000', 10);
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});

// Server graceful shutdown.
const gracefulShutdown = () => {
    console.log('Shutting down gracefully...');
    app.listen().close(() => {
        console.log('Express server closed');
        dragonflySub.close();
        dragonflyPub.close();
        console.log('Dragonfly Pub/Sub disconnected');
        process.exit(0);
    });
};

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);
