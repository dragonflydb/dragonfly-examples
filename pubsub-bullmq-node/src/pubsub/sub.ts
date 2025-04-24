import { Redis as Dragonfly } from 'ioredis';

type MessageHandler = (channel: string, message: string) => void;

export class DragonflySubscriber {
    private readonly subscriberClient: Dragonfly;
    private readonly channel: string;
    private readonly handler: MessageHandler;
    private isSubscribed = false;

    constructor(dragonfly: Dragonfly, channel: string, handler: MessageHandler) {
        this.subscriberClient = dragonfly;
        this.channel = channel;
        this.handler = handler;
        this.initialize();
    }

    private initialize() {
        this.subscriberClient.on('message', this.handler);
        this.subscriberClient.subscribe(this.channel, (err, _) => {
            if (err) {
                console.error(`failed to subscribe to channel "${this.channel}": ${err.message}`);
                return;
            }
            this.isSubscribed = true;
            console.log(`successfully subscribed to channel "${this.channel}"`);
        });
    }

    disconnect() {
        if (!this.isSubscribed) return;
        this.subscriberClient.unsubscribe();
    }
}