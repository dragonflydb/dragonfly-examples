import { Redis as Dragonfly } from 'ioredis';

export class DragonflyPublisher {
    private dragonfly: Dragonfly;
    private channel: string;

    constructor(dragonfly: Dragonfly, channel: string) {
        this.dragonfly = dragonfly;
        this.channel = channel;
    }

    publish(message: string) {
        this.dragonfly.publish(this.channel, message);
    }
}
