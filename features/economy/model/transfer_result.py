from typing import Optional
from dataclasses import dataclass


@dataclass
class TransferResult:
    success: bool
    amount: int
    sender_balance: Optional[int] = None
    receiver_balance: Optional[int] = None
    sender_name: Optional[str] = None
    receiver_name: Optional[str] = None
    message: Optional[str] = None
    
    @classmethod
    def success_result(cls, amount: int, sender_balance: int, receiver_balance: int, sender_name: str, receiver_name: str) -> 'TransferResult':
        return cls(success=True, amount=amount, sender_balance=sender_balance, receiver_balance=receiver_balance, sender_name=sender_name, receiver_name=receiver_name)
    
    @classmethod
    def failure_result(cls, message: str, amount: int = 0) -> 'TransferResult':
        return cls(success=False, amount=amount, message=message)
    
    def get_success_message(self) -> str:
        if not self.success:
            return ""
        
        return (f"💸 @{self.sender_name} перевел {self.amount} монет пользователю @{self.receiver_name}! "
                f"Баланс отправителя: {self.sender_balance} монет, "
                f"баланс получателя: {self.receiver_balance} монет.")
    
    def get_error_message(self, sender_name: str) -> str:
        if self.success:
            return ""
        
        return f"❌ @{sender_name}, {self.message}"
    
    def __str__(self) -> str:
        if not self.success:
            return f"TransferResult(success=False, message='{self.message}')"
        
        return (f"TransferResult(success=True, amount={self.amount}, "
                f"sender_balance={self.sender_balance}, receiver_balance={self.receiver_balance})") 