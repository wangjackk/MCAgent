import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { Message, MessageDocument } from '../schemas/message.schema';

@Injectable()
export class MessageRepositoryService {
  constructor(
    @InjectModel(Message.name) private messageModel: Model<MessageDocument>,
  ) {}

  async addMessage(
    message_id: string,
    message: string,
    from_member_id: string,
    chat_id: string,
    message_type: string,
    timestamp: Date,
  ): Promise<Message> {
    const newMessage = new this.messageModel({
      message_id,
      message,
      from_member_id,
      chat_id,
      message_type,
      timestamp,
    });
    return newMessage.save();
  }

  async getMessage(message_id: string): Promise<Message | null> {
    return this.messageModel.findOne({ message_id }).exec();
  }

  async getMessages(message_ids: string[]): Promise<Message[]> {
    return this.messageModel.find({ message_id: { $in: message_ids } }).exec();
  }
}
