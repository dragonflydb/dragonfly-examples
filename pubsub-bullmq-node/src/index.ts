import express from 'express';
import { Job } from 'bullmq';
import { DragonflyPublisher } from './pubsub/pub';
import { DragonflySubscriber } from './pubsub/sub';
import { DragonflyQueue } from './mq/queue';
import { DragonflyWorker } from './mq/worker';

// Express application.
const app = express();
app.use(express.json());

// Dragonfly native Pub/Sub messaging.
const pubsubChannel = 'my-pub-sub-channel';
const pubsubMessagerHandler = async (channel: string, message: string) => {
    // Simulate some relatively long-running work.
    await new Promise(resolve => setTimeout(resolve, 2000));
    console.log(`Pub/Sub message processed: ${message}`);
};
const dragonflyPub = new DragonflyPublisher(pubsubChannel);
const dragonflySub = new DragonflySubscriber(pubsubChannel, pubsubMessagerHandler);

app.post('/pub-sub-message', (req, res) => {
    dragonflyPub.publish(JSON.stringify(req.body));
    res.json({ message: 'Pub/Sub message received' });
});

// BullMQ's queue, worker, and jobs backed by Dragonfly.
const workerProcessor = async (job: Job) => {
    // Simulate some relatively long-running work.
    await new Promise(resolve => setTimeout(resolve, 2000));
}
const dragonflyQueue = DragonflyQueue.create('my-queue', { prefix: '{my-prefix}' });
const dragonflyWorker = DragonflyWorker.create('my-queue', workerProcessor, { prefix: '{my-prefix}' })
dragonflyWorker.on('completed', (job) => {
    console.log(`BullMQ job (${job.id}) completed:`, job.data);
});
dragonflyWorker.on('failed', (job, err) => {
    console.error(`BullMQ job (${job?.id}) failed:`, err);
});

app.post('/bullmq-single-job', (req, res) => {
    dragonflyQueue.add('single-job', req.body);
    res.json({ message: 'BullMQ single job received' });
});

app.post('/bullmq-delayed-job', (req, res) => {
    dragonflyQueue.add('delayed-job', req.body, { delay: 5000 });
    res.json({ message: 'BullMQ delayed job received' });
});

app.post('/bullmq-repeatable-job', (req, res) => {
    dragonflyQueue.add('repeatable-job', req.body, {
        repeat: {
            every: 5000,
            limit: 3,
        }
    });
    res.json({ message: 'BullMQ repeatable job received' });
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
