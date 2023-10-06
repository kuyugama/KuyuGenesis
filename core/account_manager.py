from inspect import iscoroutinefunction

from pyrogram import Client, types


class Account:

    _info: types.User | None
    _client: Client
    _manager: "AccountManager"

    def __init__(self, client: Client):
        self._info = None
        self._client = client

    async def resolve_info(self):
        self._info = await self._client.get_me()

        return self._info

    @property
    def info(self):
        if not self._info:
            raise ReferenceError("Info is not resolved yet. Please use Account.resolve_info() first")
        return self._info

    @property
    def client(self):
        return self._client

    @property
    def manager(self):
        return self._manager

    @manager.setter
    def manager(self, manager):
        self._manager = manager

    def __str__(self):
        if self._info:
            return f"Account(id={self._info.id}, username={self._info.username}, first_name={self._info.first_name})"


class AccountManager:

    _accounts: list[Account]

    def __init__(self):
        self._accounts = []

    def add_account(self, account: Account | Client):
        if isinstance(account, Client):
            account = Account(account)

        if not isinstance(account, Account):
            raise ValueError("Cannot operate with type {type} as account".format(type=type(account)))

        self._accounts.append(account)
        account.manager = self

    def pop_account(self, index: int) -> Account | None:
        if len(self._accounts)-1 >= index:
            account = self._accounts.pop(index)
            account.manager = None
            return account

    def get_account(self, index: int):
        if len(self._accounts)-1 >= index:
            return self._accounts[index]

    def get_accounts(self):
        return self._accounts.copy()

    def foreach(self, callback, *args, **kwargs):
        for account in self._accounts:
            callback(account, *args, **kwargs)

    async def async_foreach(self, callback, *args, **kwargs):
        iscoro = iscoroutinefunction(callback)

        for account in self._accounts:
            result = callback(account, *args, **kwargs)

            if iscoro:
                await result


class ExtendedClient(Client):
    account: Account
